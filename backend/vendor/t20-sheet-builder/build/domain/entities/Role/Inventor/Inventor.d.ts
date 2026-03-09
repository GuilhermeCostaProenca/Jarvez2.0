import { type Proficiency } from '../../Sheet';
import { SkillName } from '../../Skill';
import { Role } from '../Role';
import { type RoleAbilitiesPerLevel } from '../RoleAbilitiesPerLevel';
import { type SelectSkillGroup } from '../RoleInterface';
import { RoleName } from '../RoleName';
import { type SerializedInventor } from '../SerializedRole';
import { type PrototypeParams } from './Prototype/PrototypeEffect';
export declare class Inventor extends Role<SerializedInventor> {
    static selectSkillGroups: SelectSkillGroup[];
    static initialLifePoints: number;
    static lifePointsPerLevel: number;
    static manaPerLevel: number;
    static mandatorySkills: SkillName[];
    static proficiencies: Proficiency[];
    static readonly roleName = RoleName.inventor;
    initialLifePoints: number;
    lifePointsPerLevel: number;
    manaPerLevel: number;
    mandatorySkills: SkillName[];
    proficiencies: Proficiency[];
    readonly name = RoleName.inventor;
    abilitiesPerLevel: RoleAbilitiesPerLevel;
    constructor(chosenSkills: SkillName[][], prototypeParams: PrototypeParams);
    protected serializeSpecific(): SerializedInventor;
}
