import { PassiveEffect } from '../../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../../Sheet/TransactionInterface';
export declare class DodgeEffect extends PassiveEffect {
    static description: string;
    get description(): string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
