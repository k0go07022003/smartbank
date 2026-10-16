<!doctype html>
<html lang="pl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>@yield('title', 'Twój bank') · SmartBank</title><link rel="stylesheet" href="{{ asset('css/bank.css') }}"></head>
<body>
<header><a class="brand" href="{{ route('home') }}"><span class="brand-icon">S</span> SmartBank<span class="tag">EDU</span></a>
<nav aria-label="Nawigacja główna">
@auth
@if(auth()->user()->hasVerifiedEmail())
@if(auth()->user()->role === 'admin')<a class="{{ request()->is('admin/*')?'active':'' }}" href="{{ route('users.index') }}">Użytkownicy</a>@endif
<a class="{{ request()->routeIs('dashboard')?'active':'' }}" href="{{ route('dashboard') }}">Mój pulpit</a><a class="{{ request()->routeIs('transfer.*')?'active':'' }}" href="{{ route('transfer.create') }}">Nowy przelew</a><a class="{{ request()->routeIs('history')?'active':'' }}" href="{{ route('history') }}">Historia</a>
@endif
<form method="post" action="{{ route('logout') }}">@csrf<button class="quiet" type="submit">Wyloguj się</button></form>
@else<a href="{{ route('login') }}">Logowanie</a><a href="{{ route('register') }}">Otwórz konto</a>@endauth
</nav></header>
<main>
@if(session('status'))<div class="notice success" role="status">{{ session('status') }}</div>@endif
@if($errors->any())<div class="notice error" role="alert"><strong>Sprawdź dane formularza</strong><ul>@foreach($errors->all() as $error)<li>{{ $error }}</li>@endforeach</ul></div>@endif
@yield('content')
</main><footer><span>SmartBank © {{ date('Y') }}</span><span>Projekt edukacyjny · Wirtualne środki</span><span>PLN / Polski</span></footer>
</body></html>
