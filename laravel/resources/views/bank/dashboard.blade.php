@extends('layout')
@section('title','Mój pulpit')
@section('content')
<div class="page-head"><div><span class="eyebrow">TWÓJ PRZEGLĄD FINANSÓW</span><h1>Dzień dobry, {{ auth()->user()->name }}.</h1><p class="muted">Wszystko, czego potrzebujesz, w zasięgu ręki.</p></div><span class="badge">● Konto aktywne</span></div>
<div class="dashboard-grid"><section class="balance-card"><div class="row"><span>Rachunek osobisty</span><strong>SmartBank</strong></div><p class="muted">Dostępne środki</p><div class="balance">{{ App\Support\Money::format($account->balance) }}</div><div class="row"><code>{{ $account->number }}</code><span>PLN</span></div></section>
<section class="panel quick"><span class="eyebrow">SZYBKIE DZIAŁANIA</span><h2>Dokąd dziś<br>trafią Twoje środki?</h2><a class="button" href="{{ route('transfer.create') }}">Wykonaj przelew ↗</a><a class="text-link" href="{{ route('history') }}">Przejrzyj historię →</a></section></div>
<section class="panel"><div class="section-head"><div><span class="eyebrow">AKTYWNOŚĆ</span><h2>Ostatnie przelewy</h2></div><a href="{{ route('history') }}">Zobacz wszystkie →</a></div>@include('partials.transfers')</section>
@endsection
