import { Ability } from '../Ability/Ability';
import type { Cost } from '../Sheet/CharacterSheet/CharacterSheetInterface';
import { type SpellCircle } from './SpellCircle';
import type { SpellName } from './SpellName';
import { type SpellSchool } from './SpellSchool';
export type LearnableSpellType = 'arcane' | 'divine';
export type SpellType = LearnableSpellType | 'universal';
export declare abstract class Spell extends Ability {
    readonly name: SpellName;
    readonly circle: SpellCircle;
    readonly type: SpellType;
    static readonly circleManaCost: Record<SpellCircle, number>;
    readonly cost: Cost;
    abstract school: SpellSchool;
    abstract shortDescription: string;
    constructor(name: SpellName, circle: SpellCircle, type: SpellType);
}
