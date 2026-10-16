<?php

namespace App\Http\Controllers;

use App\Models\Account;
use App\Models\Transfer;
use App\Services\TransferService;
use App\Support\Money;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class BankController extends Controller
{
    public function dashboard(Request $request)
    {
        $account = $request->user()->account()->firstOrFail();
        $transfers = $this->history($account)->limit(5)->get();

        return view('bank.dashboard', compact('account', 'transfers'));
    }

    public function historyPage(Request $request)
    {
        $account = $request->user()->account()->firstOrFail();
        $transfers = $this->history($account)->paginate(15);

        return view('bank.history', compact('account', 'transfers'));
    }

    private function history(Account $account)
    {
        return Transfer::with(['sender.user', 'recipient.user'])->where(fn ($q) => $q->where('sender_id', $account->id)->orWhere('recipient_id', $account->id))->latest('id');
    }

    public function create(Request $request)
    {
        return view('bank.transfer', ['account' => $request->user()->account()->firstOrFail()]);
    }

    public function preview(Request $request)
    {
        $data = $request->validate([
            'recipient' => ['required', 'regex:/^SB[0-9]{10}$/', 'exists:accounts,number'],
            'amount' => ['required', 'regex:/^[0-9]{1,7}([.,][0-9]{1,2})?$/'],
            'title' => ['required', 'string', 'min:3', 'max:140'],
        ]);
        $amount = Money::cents($data['amount']);
        if ($amount < 1 || $amount > 100000000 || $amount > $request->user()->account()->firstOrFail()->balance) {
            return back()->withErrors(['amount' => 'Kwota musi wynosić od 0,01 do 1 000 000 zł i nie przekraczać salda.'])->withInput();
        }
        if ($data['recipient'] === $request->user()->account()->firstOrFail()->number) {
            return back()->withErrors(['recipient' => 'Nie możesz wykonać przelewu na własny rachunek.'])->withInput();
        }
        $request->session()->put('transfer_draft', [...$data, 'amount' => $amount, 'key' => (string) Str::uuid()]);

        return redirect()->route('transfer.confirm');
    }

    public function confirm(Request $request)
    {
        if (! $request->session()->has('transfer_draft')) {
            return redirect()->route('transfer.create');
        }

        return view('bank.confirm', ['draft' => $request->session()->get('transfer_draft')]);
    }

    public function send(Request $request, TransferService $service)
    {
        $draft = $request->session()->get('transfer_draft');
        abort_unless($draft, 419, 'Brak zlecenia. Wypełnij formularz ponownie.');
        $service->send($request->user(), $draft);
        $request->session()->forget('transfer_draft');

        return redirect()->route('history')->with('status', 'Przelew został wykonany.');
    }
}
