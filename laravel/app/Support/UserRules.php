<?php

namespace App\Support;

use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Password;

class UserRules
{
    public static function rules(?int $id = null): array
    {
        return [
            'name' => ['required', 'string', 'min:3', 'max:100', "regex:/^[\p{L} .'-]+$/u"],
            'email' => ['required', 'email', 'max:180', Rule::unique('users')->ignore($id)],
            'password' => [$id ? 'nullable' : 'required', 'confirmed', Password::min(10)->letters()->numbers(), 'max:72'],
        ];
    }
}
