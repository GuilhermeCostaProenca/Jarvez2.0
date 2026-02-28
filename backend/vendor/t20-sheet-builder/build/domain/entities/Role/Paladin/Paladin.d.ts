import { Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { RoleName } from '../RoleName';
import { type SerializedRoles } from '../SerializedRole';
export declare class Paladin extends Role {
    static selectSkillGroups: {
        amount: number;
        skills: SkillName[];
    }[];
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    static readonly roleName = RoleName.paladin;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.paladin;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills: SkillName[][]);
    protected serializeSpecific(): SerializedRoles;
}
