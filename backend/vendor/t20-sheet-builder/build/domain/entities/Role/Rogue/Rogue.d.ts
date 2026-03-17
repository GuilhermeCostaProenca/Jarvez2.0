import { type Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { RoleName } from '../RoleName';
import { type SerializedRogue } from '../SerializedRole';
export declare class Rogue extends Role<SerializedRogue> {
    static selectSkillGroups: {
        amount: number;
        skills: SkillName[];
    }[];
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    static readonly roleName = RoleName.rogue;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.rogue;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills: SkillName[][], specialistSkills: Set<SkillName>);
    protected serializeSpecific(): SerializedRogue;
}
