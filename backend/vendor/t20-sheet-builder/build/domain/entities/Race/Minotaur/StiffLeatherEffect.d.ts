import { PassiveEffect } from '../../Ability';
import { type TransactionInterface } from '../../Sheet/TransactionInterface';
export declare class StiffLeatherEffect extends PassiveEffect {
    description: string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
