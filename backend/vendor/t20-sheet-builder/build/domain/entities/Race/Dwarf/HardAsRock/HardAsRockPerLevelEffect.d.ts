import { PassiveEffect } from '../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
export declare class HardAsRockPerLevelEffect extends PassiveEffect {
    get description(): string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
