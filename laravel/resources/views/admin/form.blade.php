@extends('layout')
@section('title',$user->exists?'Edycja użytkownika':'Dodaj użytkownika')
@section('content')
<section class="narrow panel"><span class="eyebrow">PANEL ADMINISTRATORA</span><h1>{{ $user->exists?'Edytuj użytkownika':'Dodaj użytkownika' }}</h1>
<form method="post" action="{{ $user->exists?route('users.update',$user):route('users.store') }}">@csrf @if($user->exists) @method('PUT') @endif
@include('partials.identity')
<label for="role">Uprawnienia</label><select id="role" name="role" required><option value="customer" @selected(old('role',$user->role)==='customer')>Klient</option><option value="admin" @selected(old('role',$user->role)==='admin')>Administrator</option></select>
<label for="is_active">Dostęp do aplikacji</label><select id="is_active" name="is_active" required><option value="1" @selected(old('is_active',$user->is_active)==1)>Odblokowany</option><option value="0" @selected(old('is_active',$user->is_active)==0)>Zablokowany</option></select>
<p class="muted">Nowe konto oraz zmiana adresu e-mail wymagają potwierdzenia linkiem aktywacyjnym.</p><button class="full" type="submit">Zapisz użytkownika</button></form><p><a href="{{ route('users.index') }}">← Lista użytkowników</a></p></section>
@endsection
