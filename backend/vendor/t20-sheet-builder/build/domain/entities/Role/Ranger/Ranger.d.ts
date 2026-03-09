import { Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { type SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import { type SerializedRanger } from '../SerializedRole';
export declare class Ranger extends Role<SerializedRanger> {
    static selectSkillGroups: SelectSkillGroup[];
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    static readonly roleName = RoleName.ranger;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.ranger;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills: SkillName[][]);
    protected serializeSpecific(): SerializedRanger;
}
