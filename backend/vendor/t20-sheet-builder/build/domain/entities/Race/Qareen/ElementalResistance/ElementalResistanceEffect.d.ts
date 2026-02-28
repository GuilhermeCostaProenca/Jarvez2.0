import { PassiveEffect } from '../../../Ability';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import { type QareenElementalResistanceType } from '../QareenElementalResistanceType';
export declare class ElementalResistanceEffect extends PassiveEffect {
    readonly resistanceType: QareenElementalResistanceType;
    description: string;
    constructor(resistanceType: QareenElementalResistanceType);
    apply(transaction: TransactionInterface): void;
}
