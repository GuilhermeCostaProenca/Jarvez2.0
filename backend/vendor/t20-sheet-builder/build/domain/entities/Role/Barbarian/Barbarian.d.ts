import { Level, Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { Role } from '../Role';
import { type RoleAbility } from '../RoleAbility';
import { type SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import { type SerializedBarbarian } from '../SerializedRole';
export declare class Barbarian extends Role<SerializedBarbarian> {
    static readonly roleName = RoleName.barbarian;
    static readonly selectSkillGroups: SelectSkillGroup[];
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.barbarian;
    readonly abilitiesPerLevel: Record<Level, Record<string, RoleAbility>>;
    constructor(chosenSkills?: SkillName[][]);
    protected serializeSpecific(): SerializedBarbarian;
}
