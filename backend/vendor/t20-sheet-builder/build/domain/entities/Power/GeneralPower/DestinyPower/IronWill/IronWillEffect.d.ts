import { PassiveEffect } from '../../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../../Sheet/TransactionInterface';
export declare class IronWillEffect extends PassiveEffect {
    static description: string;
    get description(): string;
    apply(transaction: TransactionInterface): void;
}
