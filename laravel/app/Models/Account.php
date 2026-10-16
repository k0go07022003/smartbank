<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Account extends Model
{
    protected $fillable = ['user_id', 'number', 'balance'];

    protected function casts(): array
    {
        return ['balance' => 'integer'];
    }

    public function user()
    {
        return $this->belongsTo(User::class)->withTrashed();
    }

    public static function openFor(User $user): self
    {
        return self::create(['user_id' => $user->id, 'number' => 'SB'.str_pad((string) $user->id, 10, '0', STR_PAD_LEFT), 'balance' => 0]);
    }
}
