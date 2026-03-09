import { Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { type Spell, type SpellSchool } from '../../Spell';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { type SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import { type SerializedDruid } from '../SerializedRole';
export declare class Druid extends Role<SerializedDruid> {
    static selectSkillGroups: SelectSkillGroup[];
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    static readonly roleName = RoleName.druid;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.druid;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills: SkillName[][], chosenSpells: Spell[], chosenSchools: Set<SpellSchool>);
    protected serializeSpecific(): SerializedDruid;
}
