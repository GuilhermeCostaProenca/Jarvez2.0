import { PassiveEffect } from '../../../../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../../../../Sheet/TransactionInterface';
import { type ArcanistLineageDraconicDamageType } from './ArcanistLineageDraconicDamageType';
export declare class ArcanistLineageDraconicDamageReductionEffect extends PassiveEffect {
    readonly damageType: ArcanistLineageDraconicDamageType;
    get description(): string;
    constructor(damageType: ArcanistLineageDraconicDamageType);
    apply(transaction: TransactionInterface): void;
}
