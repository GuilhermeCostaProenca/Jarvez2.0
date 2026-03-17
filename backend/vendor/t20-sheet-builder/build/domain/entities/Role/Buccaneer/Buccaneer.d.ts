import { Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { type SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import { type SerializedBuccaneer } from '../SerializedRole';
export declare class Buccaneer extends Role<SerializedBuccaneer> {
    static readonly roleName = RoleName.buccaneer;
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static readonly mandatorySkills: SkillName[];
    static readonly proficiencies: Proficiency[];
    static readonly selectSkillGroups: SelectSkillGroup[];
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    name: RoleName;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills?: SkillName[][]);
    protected serializeSpecific(): SerializedBuccaneer;
}
