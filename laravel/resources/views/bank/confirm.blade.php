@extends('layout')
@section('title','Potwierdź przelew')
@section('content')
<section class="narrow panel"><span class="eyebrow">KROK 2 Z 2 · POTWIERDZENIE</span><h1>Sprawdź przelew</h1><dl><dt>Rachunek odbiorcy</dt><dd>{{ $draft['recipient'] }}</dd><dt>Tytuł</dt><dd>{{ $draft['title'] }}</dd><dt>Kwota</dt><dd class="balance small-balance">{{ App\Support\Money::format($draft['amount']) }}</dd></dl><form method="post" action="{{ route('transfer.send') }}">@csrf<button class="full" type="submit">Potwierdzam i wysyłam →</button></form><p><a href="{{ route('transfer.create') }}">← Wróć do formularza</a></p></section>
@endsection
