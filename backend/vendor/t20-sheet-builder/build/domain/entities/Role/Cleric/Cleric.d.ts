import { Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { type Spell } from '../../Spell';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { type SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import { type SerializedCleric } from '../SerializedRole';
export declare class Cleric extends Role<SerializedCleric> {
    static selectSkillGroups: SelectSkillGroup[];
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    static readonly roleName = RoleName.cleric;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.cleric;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills: SkillName[][], chosenSpells: Spell[]);
    protected serializeSpecific(): SerializedCleric;
}
