<?php

namespace App\Support;

class Money
{
    public static function cents(string $amount): int
    {
        $parts = explode('.', str_replace(',', '.', $amount));

        return ((int) $parts[0] * 100) + (int) str_pad($parts[1] ?? '', 2, '0');
    }

    public static function format(int $cents): string
    {
        return number_format(intdiv($cents, 100), 0, ',', ' ').','.str_pad((string) ($cents % 100), 2, '0', STR_PAD_LEFT).' zł';
    }
}
