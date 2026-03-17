import { type SerializedArcanist } from '../..';
import type { Attribute } from '../../Sheet/Attributes';
import { Level } from '../../Sheet/Level';
import type { Proficiency } from '../../Sheet/Proficiency';
import { SkillName } from '../../Skill/SkillName';
import type { Spell, SpellType } from '../../Spell/Spell';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import type { SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import type { SpellLearnFrequency } from '../SpellsAbility';
import type { ArcanistPath } from './ArcanistPath/ArcanistPath';
import { ArcanistSpells } from './ArcanistSpells/ArcanistSpells';
export declare class Arcanist<T extends ArcanistPath = ArcanistPath> extends Role<SerializedArcanist> {
    static readonly roleName = RoleName.arcanist;
    static readonly selectSkillGroups: SelectSkillGroup[];
    static get startsWithArmor(): boolean;
    static get initialLifePoints(): number;
    static get lifePointsPerLevel(): number;
    static get manaPerLevel(): number;
    static readonly mandatorySkills: SkillName[];
    static readonly proficiencies: Proficiency[];
    readonly abilitiesPerLevel: RoleAbilitiesPerLevel<{
        [Level.one]: {
            arcanistPath: ArcanistPath;
            arcanistSpells: ArcanistSpells;
        };
    }>;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.arcanist;
    initialSpells: number;
    spellType: SpellType;
    constructor(chosenSkills: SkillName[][], path: T, spells: Spell[]);
    getSpellsAttribute(): Attribute;
    getSpellLearnFrequency(): SpellLearnFrequency;
    getPath(): T;
    getInitialSpells(): Spell[];
    protected serializeSpecific(): SerializedArcanist;
}
