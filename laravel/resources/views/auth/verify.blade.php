@extends('layout')
@section('title','Aktywacja konta')
@section('content')
<section class="narrow panel"><span class="eyebrow">JESZCZE JEDEN KROK</span><h1>Sprawdź swoją pocztę</h1><p>Otwórz link aktywacyjny wysłany na <strong>{{ auth()->user()->email }}</strong>. Dopiero po potwierdzeniu adresu uzyskasz dostęp do rachunku.</p><form method="post" action="{{ route('verification.send') }}">@csrf<button type="submit">Wyślij link ponownie</button></form>
@if(app()->environment('local') && config('mail.default') === 'log')<p class="muted">Tryb lokalny: wiadomość z linkiem aktywacyjnym jest zapisywana w pliku storage/logs/laravel.log. Możesz otworzyć link również bez Internetu.</p>@endif
</section>
@endsection
