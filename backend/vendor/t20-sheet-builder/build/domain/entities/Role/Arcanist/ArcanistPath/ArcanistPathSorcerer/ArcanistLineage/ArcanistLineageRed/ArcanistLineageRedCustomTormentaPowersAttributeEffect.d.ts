import { PassiveEffect } from '../../../../../../Ability/PassiveEffect';
import { type Attribute } from '../../../../../../Sheet';
import { type TransactionInterface } from '../../../../../../Sheet/TransactionInterface';
export declare class ArcanistLineageRedCustomTormentaPowersAttributeEffect extends PassiveEffect {
    readonly attribute: Attribute;
    get description(): string;
    constructor(attribute: Attribute);
    apply(transaction: TransactionInterface): void;
}
