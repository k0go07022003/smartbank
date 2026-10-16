<?php

namespace App\Http\Controllers;

use App\Models\Account;
use App\Models\User;
use App\Support\UserRules;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class AdminUserController extends Controller
{
    public function index()
    {
        return view('admin.index', ['users' => User::with('account')->latest('id')->paginate(15)]);
    }

    public function create()
    {
        return view('admin.form', ['user' => new User(['role' => 'customer', 'is_active' => true])]);
    }

    public function store(Request $request)
    {
        $data = $this->validated($request);
        $user = DB::transaction(function () use ($data) {
            $user = User::create($data);
            Account::openFor($user);

            return $user;
        });
        event(new Registered($user));

        return redirect()->route('users.show', $user)->with('status', 'Utworzono użytkownika i wysłano link aktywacyjny.');
    }

    public function show(User $user)
    {
        return view('admin.show', compact('user'));
    }

    public function edit(User $user)
    {
        return view('admin.form', compact('user'));
    }

    public function update(Request $request, User $user)
    {
        $data = $this->validated($request, $user->id);
        if ($user->id === $request->user()->id && ($data['role'] !== 'admin' || ! $data['is_active'])) {
            return back()->withErrors(['role' => 'Nie możesz odebrać sobie dostępu administratora.']);
        }
        $emailChanged = DB::transaction(function () use ($user, $data) {
            $locked = User::whereKey($user->id)->lockForUpdate()->firstOrFail();
            $changed = $locked->email !== $data['email'];
            $locked->fill($data);
            if ($changed) {
                $locked->email_verified_at = null;
            }
            $locked->save();

            return $changed;
        });
        if ($emailChanged) {
            $user->fresh()->sendEmailVerificationNotification();
        }

        return redirect()->route('users.show', $user)->with('status', 'Zapisano zmiany.');
    }

    public function destroy(Request $request, User $user)
    {
        abort_if($user->id === $request->user()->id, 403, 'Nie możesz usunąć własnego konta.');
        DB::transaction(function () use ($user) {
            $locked = User::whereKey($user->id)->lockForUpdate()->firstOrFail();
            $account = $locked->account()->lockForUpdate()->first();
            if ($account->balance !== 0) {
                throw ValidationException::withMessages(['user' => 'Przed usunięciem użytkownika saldo musi wynosić zero.']);
            }
            $locked->delete();
        });

        return redirect()->route('users.index')->with('status', 'Usunięto użytkownika. Historia przelewów pozostaje zachowana.');
    }

    private function validated(Request $request, ?int $id = null): array
    {
        $data = $request->validate([...UserRules::rules($id), 'role' => 'required|in:customer,admin', 'is_active' => 'required|boolean']);
        if (empty($data['password'])) {
            unset($data['password']);
        }

        return $data;
    }
}
