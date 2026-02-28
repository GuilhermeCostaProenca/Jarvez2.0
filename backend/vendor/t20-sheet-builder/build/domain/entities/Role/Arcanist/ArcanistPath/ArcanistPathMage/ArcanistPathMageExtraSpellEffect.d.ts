import { PassiveEffect } from '../../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../../Sheet/TransactionInterface';
import { type Spell } from '../../../../Spell';
export declare class ArcanistPathMageExtraSpellEffect extends PassiveEffect {
    readonly spell: Spell;
    get description(): string;
    constructor(spell: Spell);
    apply(transaction: TransactionInterface): void;
}
