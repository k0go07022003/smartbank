<?php

namespace App\Providers;

use Illuminate\Auth\Notifications\VerifyEmail;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void {}

    public function boot(): void
    {
        VerifyEmail::toMailUsing(function (object $notifiable, string $url) {
            return (new MailMessage)->subject('Aktywuj konto SmartBank')
                ->greeting('Witaj, '.$notifiable->name.'!')
                ->line('Potwierdź swój adres e-mail, aby uzyskać dostęp do rachunku.')
                ->action('Aktywuj konto', $url)
                ->line('Link jest ważny przez 60 minut. Jeśli nie zakładano konta, zignoruj tę wiadomość.')
                ->salutation('Zespół SmartBank');
        });
    }
}
