<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Transfer extends Model
{
    protected $fillable = ['sender_id', 'recipient_id', 'amount', 'title', 'request_key'];

    protected function casts(): array
    {
        return ['amount' => 'integer'];
    }

    public function sender()
    {
        return $this->belongsTo(Account::class, 'sender_id');
    }

    public function recipient()
    {
        return $this->belongsTo(Account::class, 'recipient_id');
    }
}
