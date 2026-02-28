import { type SerializedWarrior } from '../..';
import { Level } from '../../Sheet/Level';
import { Proficiency } from '../../Sheet/Proficiency';
import { SkillName } from '../../Skill/SkillName';
import { Role } from '../Role';
import type { RoleAbility } from '../RoleAbility';
import type { SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
export declare class Warrior extends Role<SerializedWarrior> {
    static readonly roleName = RoleName.warrior;
    static readonly selectSkillGroups: SelectSkillGroup[];
    static get initialLifePoints(): number;
    static get lifePointsPerLevel(): number;
    static get manaPerLevel(): number;
    static readonly mandatorySkills: SkillName[];
    static readonly proficiencies: Proficiency[];
    readonly name: RoleName;
    readonly abilitiesPerLevel: Record<Level, Record<string, RoleAbility>>;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    constructor(chosenSkills: SkillName[][]);
    protected serializeSpecific(): SerializedWarrior;
}
