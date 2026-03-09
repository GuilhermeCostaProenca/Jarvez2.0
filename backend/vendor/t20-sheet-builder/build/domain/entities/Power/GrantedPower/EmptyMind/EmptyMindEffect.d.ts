import { PassiveEffect } from '../../../Ability';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
export declare class EmptyMindEffect extends PassiveEffect {
    static description: string;
    description: string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
