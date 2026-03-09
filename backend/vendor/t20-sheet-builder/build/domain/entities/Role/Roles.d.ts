import { type Proficiency } from '../Sheet';
import { type SkillName } from '../Skill';
import type { Static } from '../Static';
import type { Role } from './Role';
import type { SelectSkillGroup } from './RoleInterface';
import { RoleName } from './RoleName';
export type RoleStatic<T extends Role = Role> = Static<T, {
    roleName: RoleName;
    selectSkillGroups: SelectSkillGroup[];
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    startsWithArmor: boolean;
}>;
export declare abstract class Roles {
    static map: Record<RoleName, RoleStatic>;
    static getAll(): RoleStatic[];
    static get(roleName: RoleName): RoleStatic;
}
