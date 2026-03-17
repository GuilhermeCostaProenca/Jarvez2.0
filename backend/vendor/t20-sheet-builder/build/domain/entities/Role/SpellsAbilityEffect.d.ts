import { PassiveEffect } from '../Ability/PassiveEffect';
import type { Attribute } from '../Sheet/Attributes';
import type { Level } from '../Sheet/Level';
import { type TransactionInterface } from '../Sheet/TransactionInterface';
import type { LearnableSpellType, Spell } from '../Spell/Spell';
import { SpellCircle } from '../Spell/SpellCircle';
import type { RoleAbilityName } from './RoleAbilityName';
import type { SpellLearnFrequency } from './SpellsAbility';
export declare abstract class SpellsAbilityEffect extends PassiveEffect {
    readonly spells: Spell[];
    readonly initialSpells: number;
    readonly schools?: Set<Spell["school"]> | undefined;
    abstract spellType: LearnableSpellType;
    abstract spellsLearnFrequency: SpellLearnFrequency;
    abstract spellsAttribute: Attribute;
    abstract circleLearnLevel: Record<SpellCircle, Level>;
    constructor(spells: Spell[], initialSpells: number, source: RoleAbilityName, schools?: Set<Spell["school"]> | undefined);
    apply(transaction: TransactionInterface): void;
    private addManaModifier;
    private learnCircle;
    private learnSpells;
    private validateSpells;
}
