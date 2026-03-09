import { PassiveEffect } from '../../../Ability';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
export declare class AnalyticMindEffect extends PassiveEffect {
    static description: string;
    description: string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
