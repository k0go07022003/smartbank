<?php

namespace Tests\Feature;

use App\Models\Account;
use App\Models\User;
use App\Services\TransferService;
use Illuminate\Auth\Notifications\VerifyEmail;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Notification;
use Illuminate\Support\Facades\URL;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use Tests\TestCase;

class BankTest extends TestCase
{
    use RefreshDatabase;

    private function customer(int $balance = 0, array $attributes = []): User
    {
        $user = User::factory()->create($attributes);
        Account::openFor($user)->update(['balance' => $balance]);

        return $user;
    }

    private function draft(User $recipient, int $amount = 1234): array
    {
        return ['recipient' => $recipient->account->number, 'amount' => $amount, 'title' => 'Zwrot za obiad', 'key' => (string) Str::uuid()];
    }

    public function test_registration_hashes_password_ignores_injected_role_and_sends_activation(): void
    {
        Notification::fake();
        $this->post('/register', ['name' => 'Anna Kowalska', 'email' => 'anna@example.test', 'password' => 'Secure12345', 'password_confirmation' => 'Secure12345', 'role' => 'admin', 'balance' => 100000])
            ->assertRedirect(route('verification.notice'));
        $user = User::first();
        $this->assertTrue(Hash::check('Secure12345', $user->password));
        $this->assertSame('customer', $user->role);
        $this->assertSame(0, $user->account->balance);
        $this->assertFalse($user->hasVerifiedEmail());
        Notification::assertSentTo($user, VerifyEmail::class);
        $this->get('/dashboard')->assertRedirect(route('verification.notice'));
    }

    public function test_signed_activation_works_and_tampered_link_is_rejected(): void
    {
        $user = $this->customer(0, ['email_verified_at' => null]);
        $url = URL::temporarySignedRoute('verification.verify', now()->addMinutes(30), ['id' => $user->id, 'hash' => sha1($user->email)]);
        $this->actingAs($user)->get($url.'&tampered=1')->assertForbidden();
        $this->get($url)->assertRedirect(route('home'));
        $this->assertTrue($user->fresh()->hasVerifiedEmail());
    }

    public function test_validation_and_login_reject_invalid_input(): void
    {
        $this->post('/register', ['name' => '<script>', 'email' => 'broken', 'password' => 'a', 'password_confirmation' => 'b'])->assertSessionHasErrors(['name', 'email', 'password']);
        $this->assertDatabaseCount('users', 0);
        $this->post('/login', ['email' => "' OR 1=1 --", 'password' => 'anything'])->assertSessionHasErrors('email');
        $this->assertGuest();
    }

    public function test_login_and_role_redirects_and_logout(): void
    {
        $user = $this->customer(0, ['password' => 'Secure12345']);
        $this->post('/login', ['email' => $user->email, 'password' => 'Secure12345'])->assertRedirect(route('home'));
        $this->get('/home')->assertRedirect(route('dashboard'));
        $this->get('/admin/users')->assertForbidden();
        $this->post('/logout')->assertRedirect(route('login'));
        $this->assertGuest();
        $admin = $this->customer(0, ['role' => 'admin']);
        $this->actingAs($admin)->get('/home')->assertRedirect(route('users.index'));
    }

    public function test_blocking_user_revokes_existing_session_and_prevents_login(): void
    {
        $user = $this->customer(0, ['is_active' => false, 'password' => 'Secure12345']);
        $this->post('/login', ['email' => $user->email, 'password' => 'Secure12345'])->assertSessionHasErrors('email');
        $this->actingAs($user)->get('/dashboard')->assertRedirect(route('login'));
        $this->assertGuest();
    }

    public function test_customer_cannot_use_any_admin_crud_endpoint(): void
    {
        $user = $this->customer();
        $other = $this->customer();
        $this->actingAs($user);
        foreach (['/admin/users', '/admin/users/create', "/admin/users/{$other->id}", "/admin/users/{$other->id}/edit"] as $url) {
            $this->get($url)->assertForbidden();
        }
        $this->post('/admin/users', [])->assertForbidden();
        $this->put('/admin/users/'.$other->id, [])->assertForbidden();
        $this->delete('/admin/users/'.$other->id)->assertForbidden();
    }

    public function test_admin_crud_and_email_reverification(): void
    {
        Notification::fake();
        $admin = $this->customer(0, ['role' => 'admin']);
        $this->actingAs($admin);
        $data = ['name' => 'Jan Nowak', 'email' => 'jan@example.test', 'password' => 'Secure12345', 'password_confirmation' => 'Secure12345', 'role' => 'customer', 'is_active' => 1];
        $this->post('/admin/users', $data)->assertRedirect();
        $user = User::where('email', $data['email'])->firstOrFail();
        Notification::assertSentTo($user, VerifyEmail::class);
        $this->get('/admin/users')->assertOk()->assertSee('Jan Nowak');
        $this->get('/admin/users/create')->assertOk();
        $this->get('/admin/users/'.$user->id)->assertOk();
        $this->get('/admin/users/'.$user->id.'/edit')->assertOk();
        $user->markEmailAsVerified();
        $this->put('/admin/users/'.$user->id, [...$data, 'name' => 'Jan Kowalski', 'email' => 'nowy@example.test', 'password' => '', 'password_confirmation' => ''])->assertRedirect();
        $this->assertFalse($user->fresh()->hasVerifiedEmail());
        $this->assertTrue(Hash::check('Secure12345', $user->fresh()->password));
        $this->delete('/admin/users/'.$user->id)->assertRedirect(route('users.index'));
        $this->assertSoftDeleted('users', ['id' => $user->id]);
    }

    public function test_admin_cannot_delete_funded_user_or_remove_own_access(): void
    {
        $admin = $this->customer(0, ['role' => 'admin']);
        $user = $this->customer(100);
        $this->actingAs($admin)->delete('/admin/users/'.$user->id)->assertSessionHasErrors('user');
        $this->delete('/admin/users/'.$admin->id)->assertForbidden();
        $this->put('/admin/users/'.$admin->id, ['name' => $admin->name, 'email' => $admin->email, 'role' => 'customer', 'is_active' => 1])->assertSessionHasErrors('role');
        $this->assertSame('admin', $admin->fresh()->role);
    }

    public function test_transfer_confirmation_uses_session_and_exact_cents(): void
    {
        $alice = $this->customer(10000);
        $bob = $this->customer(2000);
        $this->actingAs($alice)->post('/transfer/preview', ['recipient' => $bob->account->number, 'amount' => '12,34', 'title' => 'Zwrot za obiad'])->assertRedirect(route('transfer.confirm'));
        $this->assertDatabaseCount('transfers', 0);
        $this->get('/transfer/confirm')->assertOk()->assertSee('12,34 zł');
        $this->post('/transfer', ['amount' => 1, 'recipient' => $alice->account->number])->assertRedirect(route('history'));
        $this->assertSame(8766, $alice->account->fresh()->balance);
        $this->assertSame(3234, $bob->account->fresh()->balance);
        $this->assertDatabaseCount('transfers', 1);
        $this->get('/history')->assertOk()->assertSee('Zwrot za obiad');
        $this->get('/dashboard')->assertOk()->assertSee('87,66 zł');
        $this->post('/transfer')->assertStatus(419);
    }

    public function test_repeated_transfer_key_never_debits_twice(): void
    {
        $alice = $this->customer(10000);
        $bob = $this->customer();
        $draft = $this->draft($bob);
        $service = app(TransferService::class);
        $service->send($alice, $draft);
        try {
            $service->send($alice, $draft);
            $this->fail('Replay accepted');
        } catch (ValidationException) {
        }
        $this->assertSame(8766, $alice->account->fresh()->balance);
        $this->assertDatabaseCount('transfers', 1);
    }

    public function test_insufficient_funds_and_blocked_or_deleted_recipient_do_not_change_balances(): void
    {
        $alice = $this->customer(1000);
        $bob = $this->customer();
        foreach (['funds', 'blocked', 'deleted'] as $case) {
            if ($case === 'blocked') {
                $bob->update(['is_active' => false]);
            }
            if ($case === 'deleted') {
                $bob->delete();
            }
            try {
                app(TransferService::class)->send($alice, $this->draft($bob, $case === 'funds' ? 1001 : 100));
                $this->fail('Invalid transfer accepted');
            } catch (ValidationException) {
            }
        }
        $this->assertSame(1000, $alice->account->fresh()->balance);
        $this->assertSame(0, $bob->account->fresh()->balance);
        $this->assertDatabaseCount('transfers', 0);
    }

    public function test_transfer_form_rejects_invalid_amounts_and_own_account(): void
    {
        $alice = $this->customer(10000);
        $bob = $this->customer();
        $this->actingAs($alice);
        foreach (['-1', '0', '0.001', '1e2', '1000001', '100,01'] as $amount) {
            $this->post('/transfer/preview', ['recipient' => $bob->account->number, 'amount' => $amount, 'title' => 'Test'])->assertSessionHasErrors('amount');
        }
        $this->post('/transfer/preview', ['recipient' => $alice->account->number, 'amount' => '1', 'title' => 'Test'])->assertSessionHasErrors('recipient');
        $this->assertDatabaseCount('transfers', 0);
    }

    public function test_history_is_private_and_escapes_transfer_title(): void
    {
        $alice = $this->customer(10000);
        $bob = $this->customer();
        $eve = $this->customer();
        app(TransferService::class)->send($alice, [...$this->draft($bob), 'title' => '<script>alert(1)</script>']);
        $this->actingAs($alice)->get('/history')->assertSee('&lt;script&gt;', false)->assertDontSee('<script>', false);
        $this->actingAs($eve)->get('/history')->assertDontSee('alert(1)');
    }

    public function test_guest_cannot_access_bank_pages(): void
    {
        foreach (['/dashboard', '/history', '/transfer', '/admin/users'] as $url) {
            $this->get($url)->assertRedirect(route('login'));
        }
    }
}
