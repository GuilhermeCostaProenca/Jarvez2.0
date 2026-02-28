import { SelectableAttributesRace } from '../../SelectableAttributesRace';
import type { Attribute, Attributes } from '../../Sheet/Attributes';
import { type SkillName } from '../../Skill';
import { RaceName } from '../RaceName';
import { type SerializedLefeu } from '../SerializedRace';
import { Deformity } from './Deformity/Deformity';
import { SonOfTormenta } from './SonOfTormenta/SonOfTormenta';
export declare class Lefeu extends SelectableAttributesRace<SerializedLefeu> {
    static readonly raceName = RaceName.lefeu;
    static attributeModifiers: Partial<Attributes>;
    readonly abilities: {
        sonOfTormenta: SonOfTormenta;
        deformity: Deformity;
    };
    private previousRace;
    /**
 * Returns an instance of lefeu race.
 * @param selectedAttributes - 3 different attributes
 * @param deformity - +2 on 2 skills
  **/
    constructor(selectedAttributes: Attribute[]);
    addDeformities(skills: SkillName[]): void;
    setPreviousRace(previousRace: RaceName): void;
    getPreviousRace(): RaceName;
    protected serializeSpecific(): SerializedLefeu;
    protected get restrictedAttributes(): string[];
    protected get fixedModifier(): number;
    protected get selectableQuantity(): number;
}
