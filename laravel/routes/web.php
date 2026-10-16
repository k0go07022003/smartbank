<?php

use App\Http\Controllers\AdminUserController;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\BankController;
use App\Http\Middleware\ActiveUser;
use App\Http\Middleware\Administrator;
use Illuminate\Foundation\Auth\EmailVerificationRequest;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::get('/', fn () => redirect()->route('home'));
Route::middleware('guest')->group(function () {
    Route::view('/login', 'auth.login')->name('login');
    Route::post('/login', [AuthController::class, 'login'])->middleware('throttle:5,1');
    Route::view('/register', 'auth.register')->name('register');
    Route::post('/register', [AuthController::class, 'register'])->middleware('throttle:5,1');
});
Route::post('/logout', [AuthController::class, 'logout'])->middleware('auth')->name('logout');
Route::middleware(['auth', ActiveUser::class])->group(function () {
    Route::view('/email/verify', 'auth.verify')->name('verification.notice');
    Route::get('/email/verify/{id}/{hash}', function (EmailVerificationRequest $request) {
        $request->fulfill();

        return redirect()->route('home')->with('status', 'Adres e-mail został potwierdzony.');
    })->middleware(['signed', 'throttle:6,1'])->name('verification.verify');
    Route::post('/email/verification-notification', function (Request $request) {
        if (! $request->user()->hasVerifiedEmail()) {
            $request->user()->sendEmailVerificationNotification();
        }

        return back()->with('status', 'Link aktywacyjny został wysłany.');
    })->middleware('throttle:3,1')->name('verification.send');
    Route::middleware('verified')->group(function () {
        Route::get('/home', fn (Request $request) => redirect()->route($request->user()->role === 'admin' ? 'users.index' : 'dashboard'))->name('home');
        Route::get('/dashboard', [BankController::class, 'dashboard'])->name('dashboard');
        Route::get('/history', [BankController::class, 'historyPage'])->name('history');
        Route::get('/transfer', [BankController::class, 'create'])->name('transfer.create');
        Route::post('/transfer/preview', [BankController::class, 'preview'])->name('transfer.preview');
        Route::get('/transfer/confirm', [BankController::class, 'confirm'])->name('transfer.confirm');
        Route::post('/transfer', [BankController::class, 'send'])->middleware('throttle:10,1')->name('transfer.send');
        Route::resource('/admin/users', AdminUserController::class)->middleware(Administrator::class);
    });
});
