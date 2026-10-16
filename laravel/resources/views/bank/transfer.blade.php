@extends('layout')
@section('title','Nowy przelew')
@section('content')
<div class="page-head"><div><span class="eyebrow">KROK 1 Z 2 · DANE PRZELEWU</span><h1>Nowy przelew</h1><p class="muted">Przekaż środki innemu klientowi SmartBank.</p></div></div>
<div class="transfer-grid"><section class="panel"><h2>Dane odbiorcy i płatności</h2><form method="post" action="{{ route('transfer.preview') }}">@csrf
<label for="recipient">Numer rachunku odbiorcy</label><input id="recipient" name="recipient" value="{{ old('recipient') }}" required pattern="SB[0-9]{10}" maxlength="12" placeholder="SB0000000003" aria-describedby="recipient-hint"><small id="recipient-hint">Wewnętrzny numer SmartBank: SB i 10 cyfr (to nie jest IBAN).</small>
<label for="amount">Kwota w PLN</label><input id="amount" name="amount" value="{{ old('amount') }}" required inputmode="decimal" placeholder="0,00" pattern="[0-9]{1,7}([.,][0-9]{1,2})?">
<label for="title">Tytuł przelewu</label><input id="title" name="title" value="{{ old('title') }}" required minlength="3" maxlength="140" placeholder="Np. zwrot za obiad">
<button class="full" type="submit">Przejdź do potwierdzenia →</button></form></section><aside class="panel summary"><span class="eyebrow">Z TWOJEGO RACHUNKU</span><h2>Rachunek osobisty</h2><code>{{ $account->number }}</code><hr><span class="muted">Dostępne środki</span><h2>{{ App\Support\Money::format($account->balance) }}</h2><p class="muted">Przed wykonaniem zobaczysz podsumowanie. Przelewy wewnętrzne są realizowane od razu.</p></aside></div>
@endsection
