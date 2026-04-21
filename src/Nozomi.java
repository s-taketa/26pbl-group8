
public class Nozomi extends Train{
	int elec;
	@Override
	public void run() {
		System.out.println("ビューン");
	}
	@Override
	public void open() {
		System.out.println("開いたよー");
	}
	@Override
	public void close() {
		System.out.println("閉まります");
	}
}
