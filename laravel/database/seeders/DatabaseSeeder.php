<?php

namespace Database\Seeders;

use App\Models\Account;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        if (! app()->environment('local', 'testing')) {
            throw new \RuntimeException('Dane demonstracyjne są dostępne tylko lokalnie.');
        }
        DB::transaction(function () {
            foreach ([['Administrator', 'admin@smartbank.test', 'admin', 0], ['Anna Kowalska', 'anna@smartbank.test', 'customer', 250000], ['Jan Nowak', 'jan@smartbank.test', 'customer', 100000]] as [$name,$email,$role,$balance]) {
                if (User::withTrashed()->where('email', $email)->exists()) {
                    continue;
                }
                $user = User::create(['name' => $name, 'email' => $email, 'password' => 'DemoBank123!', 'role' => $role]);
                $user->markEmailAsVerified();
                $account = Account::openFor($user);
                $account->update(['balance' => $balance]);
            }
        });
    }
}
