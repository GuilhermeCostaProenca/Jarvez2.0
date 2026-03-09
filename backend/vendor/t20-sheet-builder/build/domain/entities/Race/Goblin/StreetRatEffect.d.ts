import { PassiveEffect } from '../../Ability';
import { type TransactionInterface } from '../../Sheet/TransactionInterface';
export declare class StreetRatEffect extends PassiveEffect {
    description: string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
