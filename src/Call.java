
public class Call {

	public static void main(String[] args) {
		Plane b = new Boeing787();
		b.run();
		Plane w = new WrightFlyer();
		w.run();
		Train d = new D51();
		d.run();
		Train n = new Nozomi();
		n.run();
	}

}
