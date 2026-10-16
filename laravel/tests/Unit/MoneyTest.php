<?php

namespace Tests\Unit;

use App\Support\Money;
use PHPUnit\Framework\TestCase;

class MoneyTest extends TestCase
{
    public function test_decimal_strings_convert_without_floating_point_rounding(): void
    {
        $this->assertSame(29, Money::cents('0.29'));
        $this->assertSame(1230, Money::cents('12,3'));
        $this->assertSame(100, Money::cents('1'));
        $this->assertSame('1 234,56 zł', Money::format(123456));
    }
}
