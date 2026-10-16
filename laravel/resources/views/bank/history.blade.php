@extends('layout')
@section('title','Historia przelewów')
@section('content')
<div class="page-head"><div><span class="eyebrow">TWOJE TRANSAKCJE</span><h1>Historia przelewów</h1><p class="muted">Rachunek {{ $account->number }}</p></div><a class="button" href="{{ route('transfer.create') }}">Nowy przelew ↗</a></div><section class="panel">@include('partials.transfers'){{ $transfers->links('partials.pagination') }}</section>
@endsection
