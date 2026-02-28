import { type SerializedRole, type SerializedRoleBasic, type SerializedRoles } from '..';
import type { Proficiency } from '../Sheet/Proficiency';
import { type TransactionInterface } from '../Sheet/TransactionInterface';
import type { SkillName } from '../Skill/SkillName';
import { type RoleAbilitiesPerLevel } from './RoleAbilitiesPerLevel';
import type { RoleInterface, SelectSkillGroup } from './RoleInterface';
import type { RoleName } from './RoleName';
export declare abstract class Role<S extends SerializedRoles = SerializedRoles> implements RoleInterface<S> {
    readonly selectedSkillsByGroup: SkillName[][];
    readonly selectSkillGroups: SelectSkillGroup[];
    static startsWithArmor: boolean;
    static serializeBasic(role: Role): SerializedRoleBasic;
    abstract readonly initialLifePoints: number;
    abstract readonly lifePointsPerLevel: number;
    abstract readonly manaPerLevel: number;
    abstract readonly mandatorySkills: SkillName[];
    abstract readonly proficiencies: Proficiency[];
    abstract readonly name: RoleName;
    abstract readonly abilitiesPerLevel: RoleAbilitiesPerLevel;
    get startsWithArmor(): boolean;
    get chosenSkills(): SkillName[];
    /**
 * Returns an instance of this role.
 * @param chosenSkills - Chosen role skills to be trained
  **/
    constructor(selectedSkillsByGroup: SkillName[][], selectSkillGroups: SelectSkillGroup[]);
    addToSheet(transaction: TransactionInterface): void;
    addLevelOneAbilities(transaction: TransactionInterface): void;
    getTotalInitialSkills(): number;
    serialize(): SerializedRole<S>;
    protected abstract serializeSpecific(): S;
    private addLifePointsModifiers;
    private addManaPointsModifiers;
    private addProficiencies;
    private trainSkills;
    private validateChosenSkills;
}
