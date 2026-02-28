import { type TransactionInterface } from '../Sheet/TransactionInterface';
import type { AbilityName } from './Ability';
import { AbilityEffect } from './AbilityEffect';
export declare abstract class PassiveEffect extends AbilityEffect {
    constructor(source: AbilityName);
    abstract apply(transaction: TransactionInterface): void;
}
