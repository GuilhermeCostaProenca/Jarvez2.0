import { PassiveEffect } from '../../../Ability';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import { type SpellName } from '../../../Spell';
export declare class MysticTattooEffect extends PassiveEffect {
    readonly spell: SpellName;
    description: string;
    constructor(spell: SpellName);
    apply(transaction: TransactionInterface): void;
}
