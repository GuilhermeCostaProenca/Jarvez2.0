import { Level } from '../Sheet';
import type { Proficiency } from '../Sheet/Proficiency';
import type { SkillName } from '../Skill/SkillName';
import type { RoleInterface, SelectSkillGroup } from './RoleInterface';
import { RoleName } from './RoleName';
export declare class RoleFake implements RoleInterface {
    chosenSkills: SkillName[];
    abilitiesPerLevel: Record<Level, Record<string, import("./RoleAbility").RoleAbility>> & object;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    selectSkillGroups: SelectSkillGroup[];
    proficiencies: Proficiency[];
    name: RoleName;
    startsWithArmor: boolean;
    getTotalInitialSkills: import("vitest").Mock<[], number>;
    addToSheet: import("vitest").Mock<any, any>;
    serialize: import("vitest").Mock<any, any>;
}
