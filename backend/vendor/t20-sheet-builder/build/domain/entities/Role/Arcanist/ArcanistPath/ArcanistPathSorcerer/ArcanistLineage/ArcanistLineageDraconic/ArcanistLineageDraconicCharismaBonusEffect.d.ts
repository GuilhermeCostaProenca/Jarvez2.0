import { PassiveEffect } from '../../../../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../../../../Sheet/TransactionInterface';
export declare class ArcanistLineageDraconicCharismaBonusEffect extends PassiveEffect {
    get description(): string;
    constructor();
    apply(transaction: TransactionInterface): void;
}
