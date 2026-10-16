<?php

namespace App\Services;

use App\Models\Account;
use App\Models\Transfer;
use App\Models\User;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class TransferService
{
    public function send(User $sender, array $draft): Transfer
    {
        return DB::transaction(function () use ($sender, $draft) {
            $target = Account::where('number', $draft['recipient'])->first();
            if (! $target || $target->user_id === $sender->id) {
                $this->fail('Wybierz rachunek innego klienta.');
            }
            // Stała kolejność blokad ogranicza zakleszczenia równoczesnych przelewów.
            $users = User::whereIn('id', [$sender->id, $target->user_id])->orderBy('id')->lockForUpdate()->get();
            if ($users->count() !== 2 || $users->contains(fn ($u) => ! $u->is_active || ! $u->hasVerifiedEmail())) {
                $this->fail('Oba konta muszą być aktywne i zweryfikowane.');
            }
            $accounts = Account::whereIn('user_id', [$sender->id, $target->user_id])->orderBy('id')->lockForUpdate()->get();
            $source = $accounts->firstWhere('user_id', $sender->id);
            $target = $accounts->firstWhere('id', $target->id);
            if (Transfer::where('request_key', $draft['key'])->lockForUpdate()->first()) {
                $this->fail('To zlecenie zostało już wykonane.');
            }
            $amount = $draft['amount'];
            if ($amount < 1 || $amount > 100000000 || $source->balance < $amount) {
                $this->fail('Nieprawidłowa kwota lub brak środków na rachunku.');
            }
            $source->decrement('balance', $amount);
            $target->increment('balance', $amount);

            return Transfer::create(['sender_id' => $source->id, 'recipient_id' => $target->id, 'amount' => $amount, 'title' => $draft['title'], 'request_key' => $draft['key']]);
        }, 3);
    }

    private function fail(string $message): never
    {
        throw ValidationException::withMessages(['transfer' => $message]);
    }
}
