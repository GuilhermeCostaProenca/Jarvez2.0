import { type TransactionInterface } from '../../Sheet/TransactionInterface';
import { PassiveEffect } from '../PassiveEffect';
export declare class WildEmpathyRepeatedEffect extends PassiveEffect {
    description: string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
