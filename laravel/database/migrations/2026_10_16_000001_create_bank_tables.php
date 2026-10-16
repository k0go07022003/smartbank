<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->string('role')->default('customer');
            $table->boolean('is_active')->default(true);
            $table->softDeletes();
        });
        Schema::create('accounts', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->unique()->constrained()->restrictOnDelete();
            $table->string('number', 12)->unique();
            $table->unsignedBigInteger('balance')->default(0);
            $table->timestamps();
        });
        Schema::create('transfers', function (Blueprint $table) {
            $table->id();
            $table->foreignId('sender_id')->constrained('accounts')->restrictOnDelete();
            $table->foreignId('recipient_id')->constrained('accounts')->restrictOnDelete();
            $table->unsignedBigInteger('amount');
            $table->string('title', 140);
            $table->uuid('request_key')->unique();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('transfers');
        Schema::dropIfExists('accounts');
        Schema::table('users', function (Blueprint $table) {
            $table->dropColumn(['role', 'is_active', 'deleted_at']);
        });
    }
};
