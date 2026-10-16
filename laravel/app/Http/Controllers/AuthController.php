<?php

namespace App\Http\Controllers;

use App\Models\Account;
use App\Models\User;
use App\Support\UserRules;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    public function register(Request $request)
    {
        $data = $request->validate(UserRules::rules());
        $user = DB::transaction(function () use ($data) {
            $user = User::create($data);
            Account::openFor($user);

            return $user;
        });
        event(new Registered($user));
        Auth::login($user);
        $request->session()->regenerate();

        return redirect()->route('verification.notice');
    }

    public function login(Request $request)
    {
        $data = $request->validate(['email' => 'required|email', 'password' => 'required|string']);
        if (! Auth::attempt([...$data, 'is_active' => true])) {
            throw ValidationException::withMessages(['email' => 'Nieprawidłowy e-mail lub hasło albo konto jest zablokowane.']);
        }
        $request->session()->regenerate();

        return redirect()->route('home');
    }

    public function logout(Request $request)
    {
        Auth::logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect()->route('login');
    }
}
