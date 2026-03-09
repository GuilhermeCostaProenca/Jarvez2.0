import { Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { type Spell, type SpellSchool } from '../../Spell';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { type SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import { type SerializedBard } from '../SerializedRole';
export declare class Bard extends Role<SerializedBard> {
    static readonly roleName = RoleName.bard;
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    static selectSkillGroups: SelectSkillGroup[];
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.bard;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills: SkillName[][], chosenSchools: SpellSchool[], chosenSpells: Spell[]);
    protected serializeSpecific(): SerializedBard;
}
